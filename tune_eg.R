library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

MAX_TIME <- 0.94
TIME_CHECK_FREQUENCY <- 10

epm_range =           seq(0.7, 1.3, length.out = 100)
bsm_range =           seq(-0.02, -0.2, length.out = 100)
esm_range =           seq(-0.002, -0.2, length.out = 100)
eprox_range =         seq(0.05, 0.25, length.out = 100)
bprox_range =         seq(0.5, 1.5, length.out = 100)
splash_range =        seq(0.001, 0.05, length.out = 100)
stay_val_range =      seq(0.8, 1.5, length.out = 100)
max_edge_str_range =  seq(300, 400, length.out = 100)
max_stay_strn_range = seq(25, 75, length.out = 100)
falloff_range =       seq(1.8, 2.2, length.out = 100)
border_cutoff_range = seq(45, 65, length.out = 100)
stay_border_bonus_range = seq(0, 0.1, length.out = 100)
min_wait_turns_range = seq(2,7)

earlygame_max_t_range =      seq(35,36)
earlygame_order_range =      c(4,5)
earlygame_max_area_range =   seq(6,7)
earlygame_decay_range =      c(FALSE, FALSE)
earlygame_all_border_range = c(FALSE, FALSE)

sample_new_config <- function(N = 1) {
  list(
    epm =           sample(epm_range, N, TRUE),
    bsm =           sample(bsm_range, N, TRUE),
    esm =           sample(esm_range, N, TRUE),
    eprox =         sample(eprox_range, N, TRUE),
    bprox =         sample(bprox_range, N, TRUE),
    splash =        sample(splash_range, N, TRUE),
    stay_val =      sample(stay_val_range, N, TRUE),
    max_edge_str =  sample(max_edge_str_range, N, TRUE),
    max_stay_strn = sample(max_stay_strn_range, N, TRUE),
    falloff =       sample(falloff_range, N, TRUE),
    border_cutoff = sample(border_cutoff_range, N, TRUE),
    stay_border_bonus = sample(stay_border_bonus_range, N, TRUE),
    earlygame_max_t = sample(earlygame_max_t_range, N, TRUE),
    earlygame_order = sample(earlygame_order_range, N, TRUE),
    earlygame_max_area = sample(earlygame_max_area_range, N, TRUE),
    earlygame_decay = sample(earlygame_decay_range, N, TRUE),
    earlygame_all_border = sample(earlygame_all_border_range, N, TRUE),
    min_wait_turns = sample(min_wait_turns_range, N, TRUE)
  )
}

build_call <- function(dim, nopp, seed) {
  call <- paste0(
    "halite -t -s ",
    seed, " -d ",
    "\"", dim, " ", dim, "\" ",
    "\"python3 MyBot.py\" ",
    paste(rep("\"python3 MyBot2.py\"", nopp), collapse = " ")
  )
  call
}

# Run nrun randomly sampled configs against RefBot
nconf <- 36
ncore <- 36
nrun <- 1500  # 3 sec a run = 900 secs a config, 3 conf a core = 1hr
start_seed <- 33333
seeds <- seq(start_seed, start_seed + nrun- 1)

registerDoMC(ncore)
RESULTS <- as.list(seq(nconf))
for(i in seq(nconf)) {
  cat(paste(i, "-------------\n"))
  sample_conf <- sample_new_config()

  toJSON(sample_conf, auto_unbox = TRUE, pretty = TRUE) %>%
    cat(file = "dexbot.config")

  results <- foreach(seed = seeds, .combine = c) %dopar% {
    cat(".")
    winner <- build_call(20, 1, seed) %>%
      system(intern = TRUE) %>%
      paste(collapse = "\n") %>%
      str_extract("(?<=DexBot, came in rank #)[0-9]")
  }
  cat(mean(results == "1"))
  cat("\n")
  system("rm *.hlt")
  RESULTS[[i]] <- list(sample_conf, results)
}

saveRDS(RESULTS, file = "bigres3.RDS")
system("make clean")
sapply(RESULTS, function(i) mean(as.numeric(i[[2]]))) %>%
  {which(. == min(., na.rm = TRUE))}

RESULTS[[35]][[2]] %>% table
RESULTS[[29]][[2]] %>% table
RESULTS[[6]][[2]] %>% table
  # maxt, order, max area, decay, border
RESULTS[[35]] # 65, 3, 30, F, T
RESULTS[[29]] # 18, 3, 12, F, F
RESULTS[[6]]  # 62, 4, 16, F, F

'epm': 1.1,
'bsm': -0.02666667,
'esm': -0.1477778,
'eprox': 1.184848,
'bprox': 0.3757576,
'splash': 0.05979798,
'stay_val': 1.939394,
'max_edge_str': 312.1212,
'max_stay_strn': 100.5556,
'falloff': 2.09596,
'border_cutoff': 61.86869
{
  "epm": 1.054545,
  "bsm": -0.06272727,
  "esm": -0.06575758,
  "eprox": 0.1409091,
  "bprox": 0.9343434,
  "splash": 0.05878788,
  "stay_val": 0.9636364,
  "max_edge_str": 360.6061,
  "max_stay_strn": 32.92929,
  "falloff": 2.007071,
  "border_cutoff": 67.92929
}

[[1]]
[[1]]$epm
[1]

[[1]]$bsm
[1]

[[1]]$esm
[1]

[[1]]$eprox
[1]

[[1]]$bprox
[1]

[[1]]$splash
[1]

[[1]]$stay_val
[1]

[[1]]$max_edge_str
[1]

[[1]]$max_stay_strn
[1]

[[1]]$falloff
[1]

[[1]]$border_cutoff
[1]

