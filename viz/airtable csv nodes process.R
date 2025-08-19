# file: generate_nodes_from_airtable_exports.R

library(tidyverse)

# ---- 1. Load CSVs ----
dimensions <- read_csv("Dimension-Grid view.csv")
domains <- read_csv("Domains-Grid view.csv")
constructs <- read_csv("Constructs-Grid view.csv")
assessments <- read_csv("Assessments-Grid view.csv")
metrics <- read_csv("Metrics-Grid view.csv")
interventions <- read_csv("Interventions-Grid view.csv")

# ---- 2. Standardize Column Names ----
dimensions <- dimensions %>% 
  rename(name = Name) %>%
  mutate(group = "Dimension", pillars = "")

domains <- domains %>%
  rename(name = domain_name, pillars = `Lifestyle Medicine Pillars`) %>%
  mutate(group = "Domain")

constructs <- constructs %>%
  rename(name = `Construct Name`, pillars = `Lifestyle Medicine Pillar`) %>%
  mutate(group = "Construct")

assessments <- assessments %>%
  rename(name = assessment_name) %>%
  mutate(group = "Assessment", pillars = "")

metrics <- metrics %>%
  rename(name = metric_name) %>%
  mutate(group = "Metric", pillars = "")

interventions <- interventions %>%
  rename(name = intervention_name) %>%
  mutate(group = "Intervention", pillars = "")


# ---- 3. Add Pillars to All ----
constructs <- constructs %>% mutate(pillars = coalesce(pillars, ""))
assessments <- assessments %>% mutate(pillars = "")
dimensions <- dimensions %>% mutate(pillars = "")
metrics <- metrics %>% mutate(pillars = "")
interventions <- interventions %>% mutate(pillars = "")

# ---- 4. Combine into unified nodes ----
all_nodes <- bind_rows(
  dimensions %>% select(name, group, pillars),
  domains %>% select(name, group, pillars),
  constructs %>% select(name, group, pillars),
  assessments %>% select(name, group, pillars),
  metrics %>% select(name, group, pillars),
  interventions %>% select(name, group, pillars)
) %>% 
  distinct() %>% 
  mutate(
    id = row_number(),
    title = paste0("<b>", name, "</b><br>Group: ", group, ifelse(pillars != "", paste0("<br>Pillars: ", pillars), "")),
    label = name
  )

# ---- 5. Save nodes.csv ----
write_csv(all_nodes %>% select(id, label, group, pillars, title), "nodes.csv")


# Helper: get edges from a source column and multiple target columns (comma or semicolon separated)
extract_edges <- function(df, source_col, target_col, source_group) {
  df %>%
    select(source = {{source_col}}, targets = {{target_col}}) %>%
    filter(!is.na(targets)) %>%
    mutate(targets = strsplit(as.character(targets), "[;,]\\s*")) %>%
    unnest(targets) %>%
    filter(targets != "") %>%
    mutate(source_group = source_group)
}

edges_raw <- bind_rows(
  extract_edges(dimensions, name, Domain, "Dimension"),
  #extract_edges(dimensions, name, Constructs, "Dimension"),
  extract_edges(domains, name, Construct, "Domain"),
  extract_edges(domains, name, `Related Domains`, "Domain"),
  extract_edges(constructs, name, Metrics, "Construct"),
  extract_edges(constructs, name, Assessments, "Construct"),
  extract_edges(constructs, name, `Related Constructs`, "Construct"),
  extract_edges(metrics, name, `Related Assessments`, "Metric"),
  extract_edges(metrics, name, `Related Interventions`, "Metric"),
  extract_edges(interventions, name, Assessments, "Intervention"),
  extract_edges(interventions, name, Metrics, "Intervention")
)

# Map names to node IDs
name_to_id <- all_nodes %>% select(id, label)

edges_joined <- edges_raw %>%
  left_join(name_to_id, by = c("source" = "label")) %>%
  rename(from = id) %>%
  left_join(name_to_id, by = c("targets" = "label")) %>%
  rename(to = id) %>%
  filter(!is.na(from) & !is.na(to)) %>%
  select(from, to)

# ---- 6. Save edges.csv ----
write_csv(edges_joined, "edges.csv")