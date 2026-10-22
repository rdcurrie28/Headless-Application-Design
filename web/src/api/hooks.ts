import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, unwrap } from "./client";
import type { RepActionCreate, WatchlistKind } from "./types";

export type CustomerFilters = { search?: string; owner?: string; limit: number; offset: number };

export function useCustomers(filters: CustomerFilters) {
  return useQuery({
    queryKey: ["customers", filters],
    queryFn: () =>
      unwrap(
        api.GET("/v1/customers", {
          params: { query: { ...filters, search: filters.search?.trim() || undefined, owner: filters.owner || undefined } },
        }),
      ),
    placeholderData: keepPreviousData,
  });
}

export function useCustomer360(customerId: string) {
  return useQuery({
    queryKey: ["customer360", customerId],
    queryFn: () => unwrap(api.GET("/v1/customers/{customer_id}/360", { params: { path: { customer_id: customerId } } })),
  });
}

export function useWatchlist(kind: WatchlistKind, owner?: string) {
  return useQuery({
    queryKey: ["watchlist", kind, owner],
    queryFn: () => {
      const query = { query: { owner: owner || undefined, limit: 100 } };
      return kind === "at-risk"
        ? unwrap(api.GET("/v1/portfolio/at-risk", { params: query }))
        : unwrap(api.GET("/v1/portfolio/expansion", { params: query }));
    },
  });
}

export function useCreateAction(customerId: string) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: RepActionCreate) =>
      unwrap(api.POST("/v1/customers/{customer_id}/actions", { params: { path: { customer_id: customerId } }, body })),
    onSuccess: () => client.invalidateQueries({ queryKey: ["customer360", customerId] }),
  });
}
