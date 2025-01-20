FROM node:18-alpine

WORKDIR /app

# Atualiza o NPM se quiser
RUN npm install -g npm@10.9.2

# Instala as dependências
COPY package*.json ./
RUN npm install --force

# Copia o código-fonte
COPY . .

# Expondo a porta local (caso use 3000)
EXPOSE 3000

# O importante: deixe o "dev" rodar ao iniciar o container
CMD ["npm", "run", "dev"]
