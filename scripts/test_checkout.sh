#!/bin/bash
curl -s -X POST http://localhost:8084/api/v1/billing/checkout \
	-H "Content-Type: application/json" \
	-d '{"tier":"HYPERNEXUS_PROFESSIONAL_LICENSE","seats":1,"success_url":"https://hypernexus.site/success.html","cancel_url":"https://hypernexus.site/#pricing"}'
