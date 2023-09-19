if [[ ! -d "checkpoints" ]]; then
    chmod +x ./download_models.sh
    echo "Downloading models..."
    ./download_models.sh
fi
gunicorn --bind 0.0.0.0:7414 app:app