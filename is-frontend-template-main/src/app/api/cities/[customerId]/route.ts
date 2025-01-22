// src/app/api/cities/[customerId]/route.ts

import { NextRequest, NextResponse } from "next/server";

export async function PUT(req: NextRequest, context: { params: Promise<{ customerId: string }> }) {
    const { customerId } = await context.params;

    if (!customerId) {
        console.error(`Customer ID está faltando nos parâmetros da requisição.`);
        return NextResponse.json(
            { status: 400, message: 'Customer ID é obrigatório.' },
            { status: 400 }
        );
    }

    const request_body = await req.json();

    console.log(`Recebida requisição PUT para atualizar cidade com id: ${customerId}`);
    console.log(`Novos dados:`, request_body);

    const headers = {
        'Content-Type': 'application/json',
    };

    const mutation = `
        mutation UpdateCity($customerId: String!, $latitude: Float!, $longitude: Float!) {
            updateCity (customerId: $customerId, latitude: $latitude, longitude: $longitude) {
                city {
                    customerId
                    nome
                    estado
                    pais
                    regiao
                    latitude
                    longitude
                }
            }
        }
    `;

    const variables = {
        customerId: customerId,
        latitude: request_body.latitude,
        longitude: request_body.longitude
    };

    const requestBody = {
        query: mutation,
        variables
    };

    const options = {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody),
    };

    try {
        const response = await fetch(`${process.env.GRAPHQL_API_BASE_URL}/graphql/`, options);

        const data = await response.json();

        console.log(`Resposta do GraphQL:`, data);

        if (!response.ok) {
            console.error(`Erro no GraphQL: ${response.statusText}`);
            return NextResponse.json(
                { status: response.status, message: response.statusText },
                { status: response.status }
            );
        }

        if (data.errors) {
            console.error(`Erros no GraphQL: ${JSON.stringify(data.errors)}`);
            return NextResponse.json(
                { status: 400, message: data.errors },
                { status: 400 }
            );
        }

        console.log(`Cidade atualizada com sucesso:`, data);

        return NextResponse.json(data);

    } catch (error: any) {
        console.error(`Erro na requisição: ${error}`);
        return NextResponse.json(
            { status: 500, message: 'Erro Interno do Servidor' },
            { status: 500 }
        );
    }
}
