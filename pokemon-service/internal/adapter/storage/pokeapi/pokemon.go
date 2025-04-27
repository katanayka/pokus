package pokeapi

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"path"
	"strconv"
	"sync"

	"github.com/katanayka/pokus/pokemon-service/internal/core/domain"
	"github.com/katanayka/pokus/pokemon-service/internal/core/port"
)

type PokemonRepository struct {
	apiURL string
	client *http.Client
}

func (pr *PokemonRepository) fetchPokemon(ctx context.Context, identifier string) (*domain.Pokemon, error) {
	baseURL, err := url.Parse(pr.apiURL)
	if err != nil {
		return nil, fmt.Errorf("invalid api URL: %w", err)
	}

	baseURL.Path = path.Join(baseURL.Path, "pokemon", identifier)
	url := baseURL.String()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := pr.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch pokemon data: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == http.StatusNotFound {
		return nil, domain.ErrPokemonNotFound
	} else if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var pokemonData struct {
		ID     int    `json:"id"`
		Name   string `json:"name"`
		Sprite struct {
			FrontDefault string `json:"front_default"`
		} `json:"sprites"`
		Types []struct {
			Type struct {
				Name string `json:"name"`
			} `json:"type"`
		} `json:"types"`
		Stats []struct {
			Type struct {
				Name string `json:"name"`
			} `json:"stat"`
			Base int `json:"base_stat"`
		} `json:"stats"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&pokemonData); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	types := make([]string, len(pokemonData.Types))
	for i, t := range pokemonData.Types {
		types[i] = t.Type.Name
	}

	stats := make(map[string]int)
	for _, t := range pokemonData.Stats {
		stats[t.Type.Name] = t.Base
	}

	pokemon := &domain.Pokemon{
		ID:     pokemonData.ID,
		Name:   pokemonData.Name,
		Sprite: pokemonData.Sprite.FrontDefault,
		Types:  types,
		Stats:  stats,
	}
	return pokemon, nil
}

func (pr *PokemonRepository) GetByID(ctx context.Context, id int) (*domain.Pokemon, error) {
	identifier := strconv.Itoa(id)
	return pr.fetchPokemon(ctx, identifier)
}

func (pr *PokemonRepository) GetByName(ctx context.Context, name string) (*domain.Pokemon, error) {
	return pr.fetchPokemon(ctx, name)
}

func (pr *PokemonRepository) GetList(ctx context.Context, perPage, page int) ([]*domain.Pokemon, error) {
	if page <= 0 {
		return nil, fmt.Errorf("invalid page number: %d", page)
	}
	baseURL, err := url.Parse(pr.apiURL)
	if err != nil {
		return nil, err
	}
	baseURL.Path = path.Join(baseURL.Path, "pokemon")

	params := url.Values{}
	params.Add("limit", fmt.Sprintf("%d", perPage))
	params.Add("offset", fmt.Sprintf("%d", perPage*(page-1)))

	baseURL.RawQuery = params.Encode()
	url := baseURL.String()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := pr.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch pokemon data: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("unexpected status code: %d", resp.StatusCode)
	}

	var pokemonListResponse struct {
		Results []struct {
			Name string `json:"name"`
		} `json:"results"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&pokemonListResponse); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	wg := new(sync.WaitGroup)
	errors := make(chan error, len(pokemonListResponse.Results))
	pokemons := make([]*domain.Pokemon, len(pokemonListResponse.Results))
	for i, t := range pokemonListResponse.Results {
		wg.Add(1)
		go func(i int, name string) {
			defer wg.Done()
			pokemons[i], err = pr.fetchPokemon(ctx, t.Name)
			if err != nil {
				errors <- fmt.Errorf("failed to fetch pokemon data: %w", err)
				return
			}
		}(i, t.Name)
	}
	wg.Wait()

	close(errors)
	if len(errors) > 0 {
		return nil, <-errors
	}

	return pokemons, nil
}

func NewPokemonRepository(apiURL string) port.PokemonRepository {
	return &PokemonRepository{
		apiURL: apiURL,
		client: http.DefaultClient,
	}
}
