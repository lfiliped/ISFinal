// app/api/cities/[customerId]/route.ts

import { NextRequest, NextResponse } from "next/server";

export async function PUT(req: NextRequest, context: { params: { customerId: string } }) {
    // Await the params if necessary (see Next.js parameter handling below)
    const { customerId } = context.params;

    if (!customerId) {
        console.error(`Customer ID is missing in the request parameters.`);
        return NextResponse.json(
            { status: 400, message: 'Customer ID is required.' },
            { status: 400 }
        );
    }

    const request_body = await req.json();

    console.log(`Received PUT request to update city with id: ${customerId}`);
    console.log(`New data:`, request_body);

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

        console.log(`GraphQL Response:`, data);

        if (!response.ok) {
            console.error(`GraphQL Error: ${response.statusText}`);
            return NextResponse.json(
                { status: response.status, message: response.statusText },
                { status: response.status }
            );
        }

        if (data.errors) {
            console.error(`GraphQL Errors: ${JSON.stringify(data.errors)}`);
            return NextResponse.json(
                { status: 400, message: data.errors },
                { status: 400 }
            );
        }

        console.log(`City updated successfully:`, data);

        return NextResponse.json(data);

    } catch (error) {
        console.error(`Fetch Error: ${error}`);
        return NextResponse.json(
            { status: 500, message: 'Internal Server Error' },
            { status: 500 }
        );
    }
}
