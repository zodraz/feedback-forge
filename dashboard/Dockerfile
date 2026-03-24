# Dashboard Dockerfile for FeedbackForge
# Multi-stage build for smaller production image

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build arguments for API URLs (optional - defaults to localhost)
ARG VITE_API_BASE_URL
ARG VITE_AG_UI_URL

# Set as environment variables for Vite build only if provided
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_AG_UI_URL=${VITE_AG_UI_URL}

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application (Vite will use the ENV variables)
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
