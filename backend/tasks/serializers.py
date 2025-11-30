from rest_framework import serializers

class TaskInputSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)  # optional client-provided ID
    title = serializers.CharField()
    due_date = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.FloatField(required=False, allow_null=True)
    importance = serializers.IntegerField(required=False, allow_null=True, min_value=1, max_value=10)
    dependencies = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )

class TaskAnalysisSerializer(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True)
    title = serializers.CharField()
    due_date = serializers.DateField(required=False, allow_null=True)
    estimated_hours = serializers.FloatField(required=False, allow_null=True)
    importance = serializers.IntegerField(required=False, allow_null=True)
    dependencies = serializers.ListField(child=serializers.CharField())
    score = serializers.FloatField()
    priority_band = serializers.CharField()
    explanation = serializers.CharField()