# file: visualize_ontology_network.R

library(visNetwork)
library(dplyr)
library(readr)
library(htmlwidgets)

# Load updated nodes and edges
nodes <- read_csv("data/nodes.csv") %>%
  mutate(
    color.border = case_when(
      grepl("Sleep", pillars, ignore.case = TRUE)     ~ "#F4864B",
      grepl("Stress Management", pillars, ignore.case = TRUE)  ~ "#505149",
      grepl("Nutrition", pillars, ignore.case = TRUE) ~ "#B9C37A",
      grepl("Physical Activity", pillars, ignore.case = TRUE) ~ "#202926",
      grepl("Social connection", pillars, ignore.case = TRUE) ~ "#3F49A0",
      grepl("Avoidance of risky substances", pillars, ignore.case = TRUE) ~ "#FFFAF6",
      TRUE ~ "#CCCCCC"
    ),
    color.background = case_when(
      group == "Dimension"     ~ "#025E68",
      group == "Domain"        ~ "#3E5237",
      group == "Construct"     ~ "#D8EBD5",
      group == "Assessment"    ~ "#F1C6DF",
      group == "Metric"        ~ "#EBD82E",
      group == "Intervention"  ~ "#B8B5C6",
      TRUE ~ "#97C2FC"  # fallback for unexpected group
    )
  )

edges <- read_csv("data/edges.csv")

# Build interactive network
ontology_vis <- visNetwork(nodes, edges, height = "700px", width = "100%") %>%
  visEdges(arrows = "to") %>%
  visInteraction(navigationButtons = TRUE) %>%
  visOptions(highlightNearest = TRUE, selectedBy = "group", nodesIdSelection = TRUE) #%>%
  #visGroups(groupname = "Dimension", color = "#025E68") %>%
  #visGroups(groupname = "Domain", color = "#3E5237") %>%
  #visGroups(groupname = "Construct", color = "#D8EBD5") %>%
  #visGroups(groupname = "Assessment", color = "#F1C6DF") %>%
  #visGroups(groupname = "Metric", color = "#EBD82E") %>%
  #visGroups(groupname = "Intervention", color = "#B8B5C6") %>%
  #visLegend()
  


ontology_vis

group_legend <- "
<div style='font-size:13px; padding-top:10px;'>
  <b>Ontology entities:</b><br>
  <span style='background-color:#025E68; color:white; padding:2px 6px; margin:2px;'>Dimension</span>
  <span style='background-color:#3E5237; color:white; padding:2px 6px; margin:2px;'>Domain</span>
  <span style='background-color:#D8EBD5; padding:2px 6px; margin:2px;'>Construct</span>
  <span style='background-color:#F1C6DF; padding:2px 6px; margin:2px;'>Assessment</span>
  <span style='background-color:#EBD82E; padding:2px 6px; margin:2px;'>Metric</span>
  <span style='background-color:#B8B5C6; padding:2px 6px; margin:2px;'>Intervention</span>
</div>
"

ontology_vis <- ontology_vis %>%
  htmlwidgets::appendContent(htmltools::HTML(group_legend))

# Create timestamp as HTML
timestamp <- paste0("<div style='text-align:center; padding-top:10px; font-size:10px; color:#666;'>",
                    "Updated on: ", Sys.Date(), "</div>")
# Append footer to widget
ontology_vis <- ontology_vis %>%
  htmlwidgets::appendContent(htmltools::HTML(timestamp))

ontology_vis

# Save it
needs_self <- TRUE
if (!requireNamespace("rmarkdown", quietly = TRUE) ||
    !rmarkdown::pandoc_available()) {
  needs_self <- FALSE
}

htmlwidgets::saveWidget(
  ontology_vis,
  file = "index.html",
  selfcontained = needs_self,
  libdir = if (needs_self) NULL else "htmlwidgets_lib"
)