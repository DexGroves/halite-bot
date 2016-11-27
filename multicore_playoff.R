library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

build_call <- function(dim, nopp, seed) {
  call <- paste0(
    "halite -s ",
    seed, " -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 MyBot2.py\" ",
    paste(rep("\"python3 MyBot.py\"", nopp), collapse = " ")
  )
  call
}

# Run nrun randomly sampled configs against RefBot
nrun <- 2000
ncore <- 84
start_seed <- 599999
seeds <- seq(start_seed, start_seed + nrun)

registerDoMC(ncore)
results <- foreach(seed = seeds, .combine = c) %dopar% {
  cat(".")
  build_call(25, 1, seed) %>%
    system(intern = TRUE) %>%
    paste(collapse = "\n") %>%
    str_extract("(?<=DexBot, came in rank #)[0-9]")
}

table(results)
# 1198  802   untuned new algo
# 1215        tuned new algo
# 1220        tuned algo + deterministic walk
# 1364        ^ + calc fix
