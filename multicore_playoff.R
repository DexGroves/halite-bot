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
nrun <- 100
ncore <- 36
start_seed <- 44000
seeds <- seq(start_seed, start_seed + nrun)

registerDoMC(ncore)
results <- foreach(seed = seeds, .combine = c) %dopar% {
  cat(".")
  build_call(28, 1, seed) %>%
    system(intern = TRUE) %>%
    paste(collapse = "\n") %>%
    str_extract("(?<=DexBot, came in rank #)[0-9]")
}

table(results)
# 741 dc on
# 766 dc off
# 772 229 move along mine if poss
# 774 227 dc move on

#   1   2
# 742 259  config v5

#   1   2
# 739 262  config v4


#   1   2
# 756 245  config v6, no don't-walk
# results
#    1    2
# 1155  846
#
# results
#    1    2
# 1190  811  Move by vlaue

