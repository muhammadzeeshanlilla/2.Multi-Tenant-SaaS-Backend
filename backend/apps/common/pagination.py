from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
    response_message = "Results fetched successfully."

    def get_paginated_response(self, data):
        return Response({
            "success": True,
            "message": self.response_message,
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "data": data,
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "required": ["success", "message", "count", "data"],
            "properties": {
                "success": {"type": "boolean", "example": True},
                "message": {"type": "string"},
                "count": {"type": "integer", "example": 123},
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                },
                "data": schema,
            },
        }
