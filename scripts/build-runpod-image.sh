#!/bin/bash
# Build and push NEX ML Runner image for RunPod
#
# Usage:
#   ./scripts/build-runpod-image.sh                    # Build only
#   ./scripts/build-runpod-image.sh --push             # Build and push
#   ./scripts/build-runpod-image.sh --push myuser      # Build and push to myuser/nex-ml

set -e

# Configuration
IMAGE_NAME="nex-ml"
IMAGE_TAG="v1"
DOCKERFILE="docker/Dockerfile.runpod"

# Parse arguments
PUSH=false
DOCKER_USER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        *)
            DOCKER_USER="$1"
            shift
            ;;
    esac
done

# Determine full image name
if [ -n "$DOCKER_USER" ]; then
    FULL_IMAGE="$DOCKER_USER/$IMAGE_NAME:$IMAGE_TAG"
else
    FULL_IMAGE="$IMAGE_NAME:$IMAGE_TAG"
fi

echo "========================================"
echo "Building NEX ML Runner Image"
echo "========================================"
echo "Image: $FULL_IMAGE"
echo "Dockerfile: $DOCKERFILE"
echo ""

# Build
docker build -f "$DOCKERFILE" -t "$FULL_IMAGE" .

echo ""
echo "✅ Build complete: $FULL_IMAGE"

# Push if requested
if [ "$PUSH" = true ]; then
    echo ""
    echo "Pushing to Docker Hub..."
    docker push "$FULL_IMAGE"
    echo ""
    echo "✅ Pushed: $FULL_IMAGE"
    echo ""
    echo "To use in RunPod:"
    echo "  1. Create a new pod with image: $FULL_IMAGE"
    echo "  2. Or create a serverless endpoint with this image"
fi

echo ""
echo "Done!"
