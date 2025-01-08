import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    try {
        const requestBody = await req.json();
        const { xml_file_name, sort_by, order } = requestBody;

        // Validação dos parâmetros
        if (!xml_file_name || !sort_by) {
            return NextResponse.json(
                { status: 400, message: "Nome do arquivo XML e campo de ordenação são obrigatórios." },
                { status: 400 }
            );
        }

        const sortOrder = order?.toLowerCase() === "desc" ? "desc" : "asc";

        const requestOptions = {
            method: "POST",
            body: JSON.stringify({ xml_file_name, sort_by, order: sortOrder }),
            headers: { "Content-Type": "application/json" },
        };

        // Chamada para o backend REST API que, por sua vez, comunicará com o servidor gRPC
        const response = await fetch(`${process.env.REST_API_BASE_URL}/api/sort-xml/`, requestOptions);

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(
                { status: response.status, message: error.message || "Erro do backend" },
                { status: response.status }
            );
        }

        const result = await response.json();
        return NextResponse.json(result, { status: 200 });
    } catch (error) {
        console.error("Erro em /api/xml/sort-xml:", error);
        return NextResponse.json({ status: 500, message: "Erro Interno do Servidor" }, { status: 500 });
    }
}
