from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.applications.serializers import ApplicationSerializer
from apps.reminders.serializers import ReminderSerializer

from . import services


def _int_param(request, name: str, default: int, maximum: int) -> int:
    try:
        return max(1, min(int(request.query_params.get(name, default)), maximum))
    except (TypeError, ValueError):
        return default


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Everything the Dashboard page needs, in one request.

    Bundled deliberately: six separate calls on page load would each pay the
    JWT and connection cost for a handful of integers.
    """
    user = request.user
    days = _int_param(request, "days", 30, 365)
    context = {"request": request}

    return Response(
        {
            "summary": services.summary(user),
            "funnel": services.funnel(user),
            "timeline": services.timeline(user, days=days),
            "recent_applications": ApplicationSerializer(
                services.recent_applications(user), many=True, context=context
            ).data,
            "upcoming_reminders": ReminderSerializer(
                services.upcoming_reminders(user), many=True, context=context
            ).data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def summary(request):
    return Response(services.summary(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def timeline(request):
    days = _int_param(request, "days", 30, 365)
    bucket = request.query_params.get("bucket", "day")
    return Response(
        {
            "bucket": bucket,
            "days": days,
            "points": services.timeline(request.user, days=days, bucket=bucket),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def breakdowns(request):
    return Response(services.breakdowns(request.user))


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def status_timeline(request):
    days = _int_param(request, "days", 90, 365)
    return Response({"days": days, "points": services.status_timeline(request.user, days=days)})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def funnel(request):
    return Response(services.funnel(request.user))
