import React from "react";
import LeafleatMap from "./components/MainMap";
import Sidebar from "./components/MainSideBar";
import { GraphQlCities } from "./interface";

const getMapaData = async (search: string) => {
    "use server"

    const headers = {
        'Content-Type': 'application/json',
    }

    const options = {
        method: 'POST',
        headers,
        body: JSON.stringify({
            search: search
        })
    }

    const response = await fetch(`${process.env.NEXT_PUBLIC_URL}/api/cities`, options)

    if (!response.ok) {
        throw new Error(`Error fetching cities: ${response.statusText}`);
    }

    const data = await response.json();

    if (!data || !data.data || !data.data.cities) {
        throw new Error('Invalid response structure');
    }

    return data as GraphQlCities;
}

const updatePoint = async (customerId: string, latitude: number, longitude: number) => {
    "use server"

    const url = `${process.env.NEXT_PUBLIC_URL}/api/cities/${customerId}`;
    console.log(`Updating city at: ${url}`);

    const headers = {
        'Content-Type': 'application/json',
    }

    const options = {
        method: 'PUT',
        headers,
        body: JSON.stringify({
            latitude: latitude,
            longitude: longitude
        })
    }

    try {
        const response = await fetch(url, options)

        console.log(`Response status: ${response.status}`);

        if (!response.ok) {
            throw new Error(`Error updating city: ${response.statusText}`);
        }

        const data = await response.json();

        console.log(`Update response data:`, data);

        if (!data || !data.data || !data.data.update_city || !data.data.update_city.city) {
            throw new Error('Invalid response structure on update');
        }

        return data;
    } catch (error: any) {
        console.error(`Fetch Error: ${error}`);
        throw error;
    }
}

export default async function Home({ searchParams }: { searchParams: any }) {
    try {
        const params: any = await searchParams

        const search: string = params?.search ?? ''

        const mapa_data: GraphQlCities = await getMapaData(search)

        return (
            <div className="h-[100vh] w-full">
                <nav className="w-[250px] h-full absolute left-0">
                    <Sidebar searchValue={search} />
                </nav>
                <main className="h-full" style={{ marginLeft: 250 }}>
                    <LeafleatMap cities={mapa_data.data.cities} updatePoint={updatePoint} />
                </main>
            </div>
        );
    } catch (error: any) {
        console.error(error);
        return <div>Error loading cities: {error.message}</div>
    }
}
