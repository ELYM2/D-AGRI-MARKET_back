from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import uuid


def health(request):
    return JsonResponse({
        "status": "ok",
        "service": "appback",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mobile_payment(request):
    """
    Simulation d'un paiement Mobile Money / Orange Money.
    En production, cette vue devrait appeler le prestataire (MTN/Orange) et gérer les callbacks.
    Ici, on valide directement et retourne une référence simulée.
    """
    method = request.data.get("method") or request.data.get("provider")
    phone = request.data.get("phone") or request.data.get("phone_number")
    amount = request.data.get("amount")

    if method not in ["momo", "om", "MTN", "ORANGE", "MTN_MOMO", "ORANGE_MONEY"]:
        return Response({"detail": "Méthode invalide"}, status=status.HTTP_400_BAD_REQUEST)
    if not phone:
        return Response({"detail": "Numéro requis"}, status=status.HTTP_400_BAD_REQUEST)
    if not amount:
        return Response({"detail": "Montant requis"}, status=status.HTTP_400_BAD_REQUEST)

    reference = f"PM-{uuid.uuid4().hex[:10].upper()}"
    return Response({
        "status": "success",
        "reference": reference,
        "message": "Paiement simulé accepté. Veuillez confirmer sur votre téléphone.",
    })
