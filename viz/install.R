# viz/install.R
pkgs <- c("visNetwork", "dplyr", "readr", "htmlwidgets")

# Determine a user-writable library path
user_lib <- Sys.getenv("R_LIBS_USER")

if (identical(user_lib, "") || !nzchar(user_lib)) {
  # Build a sensible default for Windows/macOS/Linux
  ver_major <- R.version$major
  ver_minor <- strsplit(R.version$minor, "[.]", perl = TRUE)[[1]][1]
  ver_tag <- paste0(ver_major, ".", ver_minor)

  if (.Platform$OS.type == "windows") {
    user_home <- Sys.getenv("USERPROFILE", unset = Sys.getenv("HOME", "~"))
    user_lib <- file.path(user_home, "Documents", "R", "win-library", ver_tag)
  } else if (Sys.info()[["sysname"]] == "Darwin") {
    user_lib <- file.path("~", "Library", "R", ver_tag, "library")
  } else {
    user_lib <- file.path("~", "R", paste0(ver_tag), "library")
  }
}

# Create and use that library
dir.create(path.expand(user_lib), recursive = TRUE, showWarnings = FALSE)
.libPaths(c(path.expand(user_lib), .libPaths()))

# Install any missing packages into the user library
to_install <- setdiff(pkgs, rownames(installed.packages()))
if (length(to_install) > 0) {
  install.packages(to_install, lib = .libPaths()[1], repos = "https://cloud.r-project.org")
}

# Print where they ended up (debug)
message("Using R library paths: ", paste(.libPaths(), collapse = " | "))
