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
    "\"python3 ReferenceBot.py\" ",
    paste(rep("\"python3 MyBot.py\"", nopp), collapse = " ")
  )
  call
}

# Run nrun randomly sampled configs against RefBot
nrun <- 15
ncore <- 74
start_seed <- 3000
seeds <- seq(start_seed, start_seed + nrun)

registerDoMC(ncore)
results <- foreach(seed = seeds, .combine = c) %dopar% {
  cat(".")
  build_call(40, 3, seed) %>%
    system(intern = TRUE) %>%
    paste(collapse = "\n") %>%
    str_extract("(?<=DexBot, came in rank #)[0-9]")
}

table(results)
# results
#   1   2
# 148  53

# results m1/m2
#   1   2
# 125  76

# results just m1
#   1   2
#  70 131
# results
#   1   2   3   4   5
# 529 502 395 278 297

# HU conf
# HU: 57-18
# MW conf
# HU: 47-28
