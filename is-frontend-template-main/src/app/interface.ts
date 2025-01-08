// Representa as informações de um pedido no CSV
export interface Order {
    rowId: number; // Row ID
    orderId: string; // Order ID
    orderDate: string; // Order Date
    shipDate: string; // Ship Date
    shipMode: string; // Ship Mode
    customerId: string; // Customer ID
    customerName: string; // Customer Name
    segment: string; // Segment
    country: string; // Country
    city: string; // City
    state: string; // State
    postalCode: string; // Postal Code
    region: string; // Region
    retailSalesPeople: string; // Retail Sales People
    productId: string; // Product ID
    category: string; // Category
    subCategory: string; // Sub-Category
    productName: string; // Product Name
    returned: string; // Returned
    sales: number; // Sales
    quantity: number; // Quantity
    discount: number; // Discount
    profit: number; // Profit
    latitude?: number; // Latitude (opcional, pode estar vazio)
    longitude?: number; // Longitude (opcional, pode estar vazio)
}

// Representa uma lista de pedidos
export interface Orders {
    orders: Order[]; // Lista de pedidos
}

export interface City {
    customerId: string; 
    nome: string;
    estado: string;
    pais: string;
    regiao: string;
    latitude: number;
    longitude: number;
}

export interface UpdateCityResponse {
    data: {
        updateCity: {
            city: City;
        }
    }
}

export interface GraphQlCities {
    data: {
        cities: City[];
    }
}
