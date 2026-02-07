package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/go-chi/cors"
	"github.com/joho/godotenv"

	"github.com/puckwise/backend/internal/api"
	"github.com/puckwise/backend/internal/repository"
)

func main() {
	// Load .env file
	if err := godotenv.Load(); err != nil {
		log.Println("No .env file found, using environment variables")
	}

	// Get config from environment
	port := os.Getenv("API_PORT")
	if port == "" {
		port = "8080"
	}

	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgresql://puckwise:puckwise_dev@localhost:5432/hockey_analytics"
	}

	// Initialize database connection pool
	ctx := context.Background()
	db, err := repository.NewDB(ctx, dbURL)
	if err != nil {
		log.Fatalf("Failed to connect to database: %v", err)
	}
	defer db.Close()

	// Initialize repositories
	repos := repository.NewRepositories(db)

	// Initialize handlers
	handlers := api.NewHandlers(repos)

	// Setup router
	r := chi.NewRouter()

	// Middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.RealIP)
	r.Use(middleware.RequestID)
	r.Use(middleware.Timeout(30 * time.Second))

	// CORS
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"http://localhost:*", "http://127.0.0.1:*"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type"},
		ExposedHeaders:   []string{"Link"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	// Health check
	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("OK"))
	})

	// API routes
	r.Route("/api", func(r chi.Router) {
		// Players
		r.Route("/players", func(r chi.Router) {
			r.Get("/", handlers.ListPlayers)
			r.Get("/{id}", handlers.GetPlayer)
			r.Get("/{id}/game-log", handlers.GetPlayerGameLog)
		})

		// Projections
		r.Route("/projections", func(r chi.Router) {
			r.Get("/rankings", handlers.GetRankings)
			r.Get("/regression", handlers.GetRegressionCandidates)
		})

		// Trades
		r.Post("/trades/analyze", handlers.AnalyzeTrade)

		// Fantasy leagues
		r.Route("/leagues", func(r chi.Router) {
			r.Get("/", handlers.ListLeagues)
			r.Post("/", handlers.CreateLeague)
			r.Get("/{id}", handlers.GetLeague)
			r.Post("/{id}/teams", handlers.AddTeamToLeague)
		})

		// Fantasy teams
		r.Route("/teams", func(r chi.Router) {
			r.Get("/{id}/roster", handlers.GetTeamRoster)
			r.Post("/{id}/roster", handlers.AddPlayerToRoster)
			r.Delete("/{id}/roster/{playerId}", handlers.RemovePlayerFromRoster)
		})
	})

	// Create server
	srv := &http.Server{
		Addr:         ":" + port,
		Handler:      r,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Start server in goroutine
	go func() {
		log.Printf("Starting server on port %s", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Server error: %v", err)
		}
	}()

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}

	log.Println("Server stopped")
}
