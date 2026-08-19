FROM eclipse-temurin:21-jdk-alpine

ARG KOTLIN_VERSION=2.1.20
RUN apk add --no-cache bash curl unzip \
    && curl --fail --location --retry 3 \
      "https://github.com/JetBrains/kotlin/releases/download/v${KOTLIN_VERSION}/kotlin-compiler-${KOTLIN_VERSION}.zip" \
      --output /tmp/kotlin.zip \
    && unzip -q /tmp/kotlin.zip -d /opt \
    && rm /tmp/kotlin.zip \
    && apk del curl unzip

ENV PATH="/opt/kotlinc/bin:${PATH}"
WORKDIR /workspace
