package web

import (
	"bytes"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestWebHandlers_NoDB(t *testing.T) {
	server := NewServer(nil, nil, nil, nil, nil, nil, nil)

	t.Run("Dashboard GET nil DB", func(t *testing.T) {
		req, _ := http.NewRequest("GET", "/", nil)
		rr := httptest.NewRecorder()
		server.ServeHTTP(rr, req)

		// It should probably return 500 or handle it gracefully
		if rr.Code != http.StatusInternalServerError && rr.Code != http.StatusOK && rr.Code != http.StatusSeeOther {
			t.Errorf("Unexpected status code: %v", rr.Code)
		}
	})

	t.Run("GitHub Webhook Unauthorized", func(t *testing.T) {
		req, _ := http.NewRequest("POST", "/api/v1/webhook/github", bytes.NewBuffer([]byte(`{}`)))
		rr := httptest.NewRecorder()
		server.ServeHTTP(rr, req)

		if rr.Code == http.StatusOK {
			t.Errorf("Webhook handler returned 200 OK without valid signature")
		}
	})

    t.Run("Webhook endpoint routing", func(t *testing.T) {
		req, _ := http.NewRequest("GET", "/api/v1/webhook/github", nil)
		rr := httptest.NewRecorder()
		server.ServeHTTP(rr, req)

		// Should not be allowed
		if rr.Code != http.StatusMethodNotAllowed && rr.Code != http.StatusForbidden {
			t.Errorf("Expected MethodNotAllowed or Forbidden for GET on webhook, got %v", rr.Code)
		}
	})

    t.Run("Leads API POST nil DB", func(t *testing.T) {
		req, _ := http.NewRequest("POST", "/api/v1/leads", bytes.NewBuffer([]byte(`{"name":"test"}`)))
		req.Header.Set("Content-Type", "application/json")
		rr := httptest.NewRecorder()
		server.ServeHTTP(rr, req)

		// With a nil DB, this might return an error, but shouldn't panic
		if rr.Code == http.StatusOK {
			t.Errorf("Expected failure with nil DB")
		}
	})
}
