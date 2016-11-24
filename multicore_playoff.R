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

# Sys.setenv(PATH = paste(Sys.getenv("PATH"),
#                         "/nas/isg_prodops_work/dgrov/projects/halsrc",
#                          sep = ":"))

# Run nrun randomly sampled configs against RefBot
nrun <- 20
ncore <- 20
seeds <- seq(2000, 2000 + nrun)

registerDoMC(ncore)
results <- foreach(seed = seeds, .combine = c) %dopar% {
  cat(".")
  build_call(25, 1, seed) %>%
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
