import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
    // Extrai os arquivos enviados no formulário
    const formData = await req.formData();
    const body = Object.fromEntries(formData);
    const file = (body.file as Blob) || null;
    const dtd_file = (body.dtd_file as Blob) || null;

    // Verifica se os arquivos foram enviados
    if (!file || !dtd_file) {
        return NextResponse.json({ status: 500, message: 'Files not sent!' }, { status: 500 });
    }

    const formdata = new FormData();
    formdata.append("file", file);
    formdata.append("file_dtd", dtd_file);

    const requestOptions = {
        method: "POST",
        body: formdata,
    };

    try {
        // Faz a requisição para o backend REST
        const response = await fetch(`${process.env.NEXT_PUBLIC_REST_API_BASE_URL}/api/upload-file/by-chunks`, requestOptions);

        if (!response.ok) {
            // Retorna o erro caso a requisição falhe
            return NextResponse.json({ status: response.status, message: response.statusText }, { status: response.status });
        }

        // Retorna a resposta JSON do backend
        return NextResponse.json(await response.json());
    } catch (e: unknown) {
        console.error("Error during upload:", e);
        
        // Verifica se 'e' é uma instância de Error
        if (e instanceof Error) {
            return NextResponse.json({ status: 500, message: e.message }, { status: 500 });
        }

        // Caso contrário, trata 'e' como uma string genérica
        return NextResponse.json({ status: 500, message: 'An unknown error occurred.' }, { status: 500 });
    }
}
