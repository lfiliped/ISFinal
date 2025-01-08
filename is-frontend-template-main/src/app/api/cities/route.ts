// src/app/api/cities/route.ts

import { NextRequest, NextResponse } from "next/server";
import { GraphQlCities } from "../../interface";

export async function POST(req: NextRequest) {
    const request_body = await req.json();
    const city = request_body?.search ?? '';

    const headers = {
        'Content-Type': 'application/json',
    };

    const query = `
        query Cities($nome: String) {
            cities(nome: $nome) {
                customerId
                nome
                estado
                pais
                regiao
                latitude
                longitude
            }
        }
    `;

    const variables = {
        nome: city
    };

    const requestBody = {
        query,
        variables
    };

    const options = {
        method: 'POST',
        headers,
        body: JSON.stringify(requestBody),
    };

    try {
        const response = await fetch(`${process.env.GRAPHQL_API_BASE_URL}/graphql/`, options);

        if (!response.ok) {
            console.error(`GraphQL Error: ${response.statusText}`);
            return NextResponse.json(
                { status: response.status, message: response.statusText },
                { status: response.status }
            );
        }

        const data = await response.json();

        if (data.errors) {
            console.error(`GraphQL Errors: ${JSON.stringify(data.errors)}`);
            return NextResponse.json(
                { status: 400, message: data.errors },
                { status: 400 }
            );
        }

        return NextResponse.json(data);

    } catch (error) {
        console.error(`Fetch Error: ${error}`);
        return NextResponse.json(
            { status: 500, message: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
