package download

import (
	"bytes"
	"io"
	"net/http"
)

type roundTripFunc func(*http.Request) (*http.Response, error)

func (function roundTripFunc) RoundTrip(request *http.Request) (*http.Response, error) {
	return function(request)
}

func fixtureClient(data []byte) *http.Client {
	return &http.Client{Transport: roundTripFunc(func(_ *http.Request) (*http.Response, error) {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(bytes.NewReader(data)),
			Header:     make(http.Header),
		}, nil
	})}
}
