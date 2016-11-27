library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

build_call <- function(dim, nopp, seed) {
  call <- paste0(
    "halite -t -s ",
    seed, " -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 ReferenceBot.py\" ",
    paste(rep("\"python3 MyBot.py\"", nopp), collsapse = " ")
  )
  call
}

# Run nrun randomly sampled configs against RefBot
nrun <- 2000
ncore <- 38
start_seed <- 299999
seeds <- seq(start_seed, start_seed + nrun)

registerDoMC(ncore)
results <- foreach(seed = seeds, .combine = c) %dopar% {
  cat(".")
  res <- build_call(28, 1, seed) %>%
    system(intern = TRUE) %>%
    paste(collapse = "\n") %>%
    str_extract("(?<=DexBot, came in rank #)[0-9]")
  if (!res %in% c("1", "2")) {
    cat("ERR!")
    system("tail `ls | grep log |tail -1`", intern = TRUE) %>%
      cat
  }
  res
}

table(results)
# 1198  802   untuned new algo
