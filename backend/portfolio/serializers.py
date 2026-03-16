from rest_framework import serializers

from .models import Holding, PriceHistory, Security, TradeHistory


class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Security
        fields = [
            "id",
            "symbol",
            "name",
            "security_type",
            "exchange",
            "currency",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class HoldingSerializer(serializers.ModelSerializer):
    security_symbol = serializers.CharField(source="security.symbol", read_only=True)
    security_name = serializers.CharField(source="security.name", read_only=True)
    account_name = serializers.CharField(source="account.name", read_only=True, default=None)

    class Meta:
        model = Holding
        fields = [
            "id",
            "user",
            "account",
            "account_name",
            "security",
            "security_symbol",
            "security_name",
            "shares",
            "cost_basis",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]
        extra_kwargs = {"account": {"required": False, "allow_null": True}}

    def validate_account(self, value):
        if value is not None:
            request = self.context.get("request")
            if request and value.user != request.user:
                raise serializers.ValidationError("Invalid account.")
            if value.account_type != "investment":
                raise serializers.ValidationError(
                    "Holdings can only be added to investment accounts."
                )
        return value


class PriceHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceHistory
        fields = [
            "id",
            "security",
            "date",
            "open_price",
            "close_price",
            "high_price",
            "low_price",
            "volume",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class TradeHistorySerializer(serializers.ModelSerializer):
    security_symbol = serializers.CharField(source="security.symbol", read_only=True)

    class Meta:
        model = TradeHistory
        fields = [
            "id",
            "user",
            "account",
            "security",
            "security_symbol",
            "date",
            "trade_type",
            "shares",
            "price_per_share",
            "fees",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def validate_account(self, value):
        if value is not None:
            request = self.context.get("request")
            if request and value.user != request.user:
                raise serializers.ValidationError("Invalid account.")
        return value
