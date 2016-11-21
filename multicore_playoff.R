library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

build_call <- function(dim, nopp) {
  call <- paste0(
    "halite -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 MyBot.py\" ",
    paste(rep("\"python3 ReferenceBot.py\"", nopp), collapse = " ")
  )
  call
}

# Run nrun randomly sampled configs against RefBot ---------------------------
nrun <- 1000
ncore <- 20

registerDoMC(ncore)
results <- foreach(i = seq(nrun), .combine = c) %dopar% {
  cat(".")
  build_call(30, 1) %>%
    system(intern = TRUE) %>%
    paste(collapse = "\n") %>%
    str_extract("(?<=DexBot, came in rank #)[0-9]")
}

table(results)
