ARG NODE_IMAGE=node:20-alpine
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
ARG NEXT_PUBLIC_DEFAULT_PROJECT_PATH=/app/app
FROM ${NODE_IMAGE} AS deps

WORKDIR /app

# Install dependencies from the lockfile first so Docker can reuse this layer
# when only application source changes. npm ci also fails fast if package.json
# and package-lock.json drift apart, which keeps container builds reproducible.
COPY package.json package-lock.json ./
RUN npm ci

FROM ${NODE_IMAGE} AS builder

WORKDIR /app
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_DEFAULT_PROJECT_PATH
# NEXT_PUBLIC values are compiled into the browser bundle by Next.js, so Docker
# must provide them during the build stage instead of only at container runtime.
ENV NEXT_TELEMETRY_DISABLED=1 \
    NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL} \
    NEXT_PUBLIC_DEFAULT_PROJECT_PATH=${NEXT_PUBLIC_DEFAULT_PROJECT_PATH}

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM ${NODE_IMAGE} AS runner

WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=3000

# Keep the runtime image small by copying only the built Next.js application,
# production dependencies, and package metadata needed by `next start`.
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/package-lock.json ./package-lock.json
COPY --from=builder /app/next.config.ts ./next.config.ts
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

CMD ["npm", "run", "start"]
