"use client"

import React, { useEffect, useRef, useState } from 'react';
import { LayerGroup, LayersControl, MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css";
import "leaflet-defaulticon-compatibility";
import { City } from '../interface';
import L from 'leaflet';
import Supercluster from 'supercluster';
import { toast } from 'react-toastify';

const LeafleatMap = ({ cities, updatePoint } : { cities: City[], updatePoint: (customerId: string, latitude: number, longitude: number) => any }) => {
    const [clusters, setClusters]   = useState<any[]>([])
    const mapRef                    = useRef<any>(null)

    const superclusterRef = useRef(
        new Supercluster({
            radius: 40, // Cluster radius in pixels
            maxZoom: 20, // Max zoom for clustering
        })
    )
      
    const updateClusters = (map: { getBounds: () => any; getZoom: () => any; }) => {
        const bounds    = map.getBounds();
        const zoom      = map.getZoom();
    
        const bbox: any = [
            bounds.getWest(),
            bounds.getSouth(),
            bounds.getEast(),
            bounds.getNorth(),
        ];
    
        const clusters: any = superclusterRef.current.getClusters(bbox, zoom)
        

        setClusters(clusters)

        return
    }
    
    useEffect(() => {
        const geoJSONPlaces = cities.map(place => {
            const geoJSONPlace: any = {
                type: "Feature",
                properties: {
                    customerId: place.customerId,
                    nome: place.nome,
                    estado: place.estado,
                    pais: place.pais,
                    regiao: place.regiao,
                    latitude: place.latitude,
                    longitude: place.longitude
                },
                geometry: {
                    type: "Point",
                    coordinates: [place.longitude, place.latitude]
                }
            }

            return geoJSONPlace
        })

        superclusterRef.current.load(geoJSONPlaces); 

        if(!mapRef.current) {
            setTimeout(() => {
                const mapInstance = mapRef.current;
                updateClusters(mapInstance)
            }, 100)
        }

    }, [cities])

    const MapEvents = () => {
        const map = useMap()

        map.on("moveend", () => updateClusters(map))
        
        return null
    }

    const onHandleDragMarkerOver = async (e: any, customerId: string) => {
        const _lat = e.target._latlng.lat
        const _lng = e.target._latlng.lng

        try {
            const promise_update = await updatePoint(customerId, _lat, _lng)

            // Verifica se a resposta contém status de erro
            if(promise_update.status){
                console.error(promise_update)
                toast.error('Erro ao salvar os dados.')
                return
            }

            // Extraia os dados atualizados da resposta
            const updatedCity = promise_update.data.update_city.city

            // Encontre o índice do cluster correspondente
            const idx = clusters.findIndex((cluster: { properties: {customerId: string} }) => String(cluster.properties.customerId) === String(customerId))

            if(idx > -1){
                const new_clusters: any[] = [...clusters]

                new_clusters[idx].properties = {
                    ...new_clusters[idx].properties,
                    // Atualiza os campos com os dados retornados
                    nome: updatedCity.nome,
                    estado: updatedCity.estado,
                    pais: updatedCity.pais,
                    regiao: updatedCity.regiao,
                    latitude: updatedCity.latitude,
                    longitude: updatedCity.longitude
                }

                new_clusters[idx].geometry = {
                    ...new_clusters[idx].geometry,
                    coordinates: [updatedCity.longitude, updatedCity.latitude]
                }

                setClusters(new_clusters)
                toast.success('Cidade atualizada com sucesso!')
            }
        } catch (error: any) {
            
        } finally {
            // Recarregar a página completamente, independentemente do sucesso ou erro
            window.location.reload()
        }
    }

    return (
        <MapContainer
            center={[0, 0]}
            zoom={3}
            scrollWheelZoom={true}
            style={{ height: "100%", width: "100%" }}
            className='relative'
            ref={mapRef}
        >
            <LayersControl position="topright">
                {/* Base Layers */}
                <LayersControl.BaseLayer checked name="OpenStreetMap">
                    <TileLayer
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    />
                </LayersControl.BaseLayer>

                <LayersControl.BaseLayer name="CartoDB Positron">
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://www.carto.com/">CARTO</a>'
                    />
                </LayersControl.BaseLayer>

                <LayersControl.BaseLayer name="Dark Map">
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://www.carto.com/">CARTO</a>'
                    />
                </LayersControl.BaseLayer>
            
                <LayersControl.Overlay checked name="Cities">
                    <LayerGroup>
                        {clusters.map((cluster: any) => {
                            const [lng, lat] = cluster.geometry.coordinates;
                            const { cluster: isCluster, point_count: pointCount, cluster_id } = cluster.properties;

                            if (isCluster) {
                                return (
                                    <Marker
                                        key={`cluster-${cluster_id}`}
                                        position={[lat, lng]}
                                        icon={L.divIcon({
                                            html: `<div style="background-color:rgba(0, 123, 255, 0.8); color: white; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center;">
                                                ${pointCount}
                                            </div>`,
                                            className: "cluster-marker",
                                            iconSize: [30, 30],
                                        })}
                                    />
                                );
                            }

                            return (
                                <Marker
                                    key={`marker-${cluster.properties.customerId}`}
                                    position={[lat, lng]}
                                    draggable={true}
                                    eventHandlers={{
                                        dragend: (e) => onHandleDragMarkerOver(e, cluster.properties.customerId),
                                    }}
                                >
                                    <Popup>
                                        <div>
                                            <p><strong>customerId:</strong> {cluster.properties.customerId}</p>
                                            <p><strong>Nome:</strong> {cluster.properties.nome}</p>
                                            <p><strong>Estado:</strong> {cluster.properties.estado}</p>
                                            <p><strong>País:</strong> {cluster.properties.pais}</p>
                                            <p><strong>Região:</strong> {cluster.properties.regiao}</p>
                                            <p><strong>Lat:</strong> {cluster.properties.latitude}</p>
                                            <p><strong>Lng:</strong> {cluster.properties.longitude}</p>
                                        </div>
                                    </Popup>
                                </Marker>
                            );
                        })}
                    </LayerGroup>
                </LayersControl.Overlay>
            </LayersControl>
               
            <MapEvents />
        </MapContainer>
    );

};

export default LeafleatMap;
