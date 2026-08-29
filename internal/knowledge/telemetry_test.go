package knowledge

import (
	"testing"
    "net/http"
    "net/http/httptest"

	"gitlab.com/robertpelloni/marketing_agent/internal/web"
)

func TestTelemetryWebSocketEndpoint_Exists(t *testing.T) {
    server := web.NewServer(nil, nil, nil, nil, nil, nil, nil)

    // Test that the endpoint is registered (doesn't 404)
    req, _ := http.NewRequest("GET", "/ws/telemetry", nil)
    // Add WebSocket upgrade headers to simulate a client request
    req.Header.Set("Connection", "Upgrade")
    req.Header.Set("Upgrade", "websocket")
    req.Header.Set("Sec-WebSocket-Version", "13")
    req.Header.Set("Sec-WebSocket-Key", "dGhlIHNhbXBsZSBub25jZQ==")

    rr := httptest.NewRecorder()
    server.ServeHTTP(rr, req)

    // Status should be 101 Switching Protocols, or 401 if auth middleware blocks it, or 500 if DB is nil
    // As long as it's not 404, the endpoint exists
    if rr.Code == http.StatusNotFound {
        t.Errorf("Telemetry WebSocket endpoint not found")
    }
}
