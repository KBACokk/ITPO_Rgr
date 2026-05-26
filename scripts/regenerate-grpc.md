# Перегенерация gRPC-кода

Если вы изменили файлы `.proto` в директории `proto/`, вам необходимо перегенерировать Python-код (файлы `*_pb2.py` и `*_pb2_grpc.py`).

## Команда для генерации

Убедитесь, что у вас установлены необходимые пакеты из `requirements.txt` (включая `grpcio-tools`).

Выполните следующую команду из корня репозитория:

```bash
python -m grpc_tools.protoc -I ./proto --python_out=./gen --pyi_out=./gen --grpc_python_out=./gen ./proto/bookings.proto ./proto/availability.proto
```

После этого новые сгенерированные файлы появятся в директории `gen/`.
