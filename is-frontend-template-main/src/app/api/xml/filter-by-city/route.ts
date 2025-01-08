import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    try {
        const requestBody = await req.json();
        const { xml_file_name, search_term } = requestBody;

        if (!xml_file_name || !search_term) {
            return NextResponse.json(
                { status: 400, message: "XML file name and search term are required." },
                { status: 400 }
            );
        }

        const requestOptions = {
            method: "POST",
            body: JSON.stringify({ xml_file_name, search_term }),
            headers: { "Content-Type": "application/json" },
        };

        const response = await fetch(`${process.env.REST_API_BASE_URL}/api/xml-text-search/`, requestOptions);

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(
                { status: response.status, message: error.message || "Error from backend" },
                { status: response.status }
            );
        }

        const result = await response.json();
        return NextResponse.json(result, { status: 200 });
    } catch (error) {
        console.error("Error in /api/xml-text-search:", error);
        return NextResponse.json({ status: 500, message: "Internal Server Error" }, { status: 500 });
    }
}
