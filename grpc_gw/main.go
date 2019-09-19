package main

import (
	"flag"
	"fmt"
	"io"
	"net/http"
	_ "path"
	"strings"
	"time"

	redoc_mw "github.com/go-openapi/runtime/middleware"
	"github.com/golang/glog"
	"github.com/grpc-ecosystem/grpc-gateway/runtime"
	"github.com/sirupsen/logrus"
	"golang.org/x/net/context"
	"google.golang.org/grpc"

	wallets_gw "gitlab.com/bonum/py-wallets/grpc_gw/proto"
)

var (
	echoEndpoint = flag.String("endpoint", "0.0.0.0:50051", "endpoint of wallets service")
	swaggerPath  = flag.String("swagger", "wallets.swagger.json", "swagger.json")
)

func loggingMW(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		entry := logrus.WithField("URI", r.RequestURI)
		defer func() { entry.WithField("time", time.Since(time.Now())).Info("completed") }()
		entry.Infof("serving %v", r.RequestURI)
		h.ServeHTTP(w, r)
	})
}

func swaggerMW(h http.Handler) http.Handler {
	return redoc_mw.Redoc(redoc_mw.RedocOpts{
		BasePath: "/docs",
		Path:     "/",
		SpecURL:  "/swagger.json",
	}, h)
}

// newGateway returns a new gateway server which translates HTTP into gRPC.
func newGateway(ctx context.Context, opts ...runtime.ServeMuxOption) (http.Handler, error) {
	customMarshaller := &runtime.JSONPb{
		OrigName:     true,
		EmitDefaults: true,
	}
	muxOpt := runtime.WithMarshalerOption(runtime.MIMEWildcard, customMarshaller)
	mux := runtime.NewServeMux(muxOpt)
	dialOpts := []grpc.DialOption{grpc.WithInsecure()}
	err := wallets_gw.RegisterWalletsHandlerFromEndpoint(ctx, mux, *echoEndpoint, dialOpts)
	if err != nil {
		return nil, err
	}
	return mux, nil
}

// allowCORS allows Cross Origin Resource Sharing from any origin.
// Don't do this without consideration in production systems.
func allowCORS(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Max-Age", "3600")
		w.Header().Set("Content-Type", "*/*")
		if origin := r.Header.Get("Origin"); origin != "" {
			w.Header().Set("Access-Control-Allow-Origin", origin)
			w.Header().Set("Access-Control-Max-Age", "3600")
			if r.Method == "OPTIONS" && r.Header.Get("Access-Control-Request-Method") != "" {
				preflightHandler(w, r)
				return
			}
		}
		h.ServeHTTP(w, r)
	})
}

func preflightHandler(w http.ResponseWriter, r *http.Request) {
	headers := []string{"Content-Type", "Accept"}
	w.Header().Set("Access-Control-Allow-Headers", strings.Join(headers, ","))
	methods := []string{"GET", "HEAD", "POST", "PUT", "DELETE"}
	w.Header().Set("Access-Control-Allow-Methods", strings.Join(methods, ","))
	w.Header().Set("Access-Control-Max-Age", "3600")
	return
}

// Run starts a HTTP server and blocks forever if successful.
func Run(address string, opts ...runtime.ServeMuxOption) error {
	ctx := context.Background()
	ctx, cancel := context.WithCancel(ctx)
	defer cancel()

	mainMux := http.NewServeMux()

	data, err := readSwaggerJSON(*swaggerPath)
	if err != nil {
		logrus.Error(err)
	}
	mainMux.HandleFunc("/swagger.json", func(w http.ResponseWriter, req *http.Request) {
		io.Copy(w, strings.NewReader(string(data)))
	})
	mainMux.HandleFunc("/", func(w http.ResponseWriter, req *http.Request) {
		url := fmt.Sprintf("https://generator.swagger.io/?url=http://localhost:8081/swagger.json")
		http.Redirect(w, req, url, 301)
	})

	gw, err := newGateway(ctx, opts...)
	if err != nil {
		return err
	}

	// mainMux.Handle("/", gw)
	mainMux.Handle("/api/v1/", http.StripPrefix("/api/v1", gw))

	handler := loggingMW(allowCORS(mainMux))
	handler = swaggerMW(handler)
	srv := &http.Server{
		Handler:      handler,
		Addr:         address,
		WriteTimeout: 3 * time.Second,
		ReadTimeout:  3 * time.Second,
	}
	// scs := spew.NewDefaultConfig()
	// scs.DisablePointerAddresses = true
	// scs.Dump(srv.Handler)

	return srv.ListenAndServe()
}

func main() {
	port := "0.0.0.0:8081"
	flag.Parse()
	logrus.Infof("Starting on port %v", port)
	defer glog.Flush()

	if err := Run(port); err != nil {
		logrus.Fatal(err)
	}
}
