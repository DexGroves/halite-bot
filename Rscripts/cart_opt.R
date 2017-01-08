library("jsonlite")
library("data.table")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

epm                  = 1.012121
bsm                  = -0.05808081
esm                  = -0.05474747
eprox                = 0.1344444
bprox                = 0.8737374
splash               = 0.01747475
stay_val             = 1.216667
max_edge_str         = 338.3838
max_stay_strn        = 25.90909
falloff              = 2.043434
border_cutoff        = 60.85859
stay_border_bonus    = 0.0
min_wait_turns       = 3

earlygame_max_t      = 62
earlygame_decay      = FALSE
earlygame_order      = 3
earlygame_max_area   = 16
earlygame_all_border = FALSE

nopp <- c(1, 3)
dim <- c(20, 40)

base_table <- data.table(
  expand.grid(
    epm = epm,
    bsm = bsm,
    esm = esm,
    eprox = eprox,
    bprox = bprox,
    splash = splash,
    stay_val = stay_val,
    stay_border_bonus = stay_border_bonus,
    max_edge_str = max_edge_str,
    max_stay_strn = max_stay_strn,
    falloff = falloff,
    border_cutoff = border_cutoff,
    earlygame_max_t = earlygame_max_t,
    earlygame_decay = earlygame_decay,
    earlygame_order = earlygame_order,
    earlygame_max_area = earlygame_max_area,
    earlygame_all_border = earlygame_all_border,
    min_wait_turns = min_wait_turns,
    nopp = nopp,
    dim = dim
  )
)

Rearlygame_max_t      = c(5, 15, 30, 90)
Rearlygame_decay      = c(TRUE, FALSE)
Rearlygame_order      = c(2, 3, 5, 7)
Rearlygame_max_area   = c(4, 8, 16, 32)
Rearlygame_all_border = c(TRUE, FALSE)
Rmin_wait_turns       = c(3, 5)

extend_base <- function(table, varname, values) {
  set_varname_to_val <- function(table, varname, value) {
    table <- copy(table)
    table[, eval(varname) := value]
    table
  }
  values %>%
    lapply(set_varname_to_val, table = table, varname = varname) %>%
    rbindlist
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

configs <- rbind(
  extend_base(base_table, "earlygame_max_t", Rearlygame_max_t),
  extend_base(base_table, "earlygame_decay", Rearlygame_decay),
  extend_base(base_table, "earlygame_order", Rearlygame_order),
  extend_base(base_table, "earlygame_max_area", Rearlygame_max_area),
  extend_base(base_table, "earlygame_all_border", Rearlygame_all_border),
  extend_base(base_table, "min_wait_turns", Rmin_wait_turns)
)


ncore <- 70
nrun <- 500
start_seed <- 1234

configs <- configs[sample(nrow(configs), nrow(configs))]
SEEDS <- seq(start_seed, start_seed + nrun - 1)
RESULTS <- as.list(seq(nrun))
registerDoMC(ncore)
for (i in seq(nrow(configs))) {
  config <- as.list(configs[i, ])

  toJSON(config, auto_unbox = TRUE, pretty = TRUE) %>%
    cat(file = "dexbot.config")

  results <- foreach(seed = SEEDS, .combine = c) %dopar% {
    cat(".")
    winner <- build_call(config$dim, config$nopp, seed) %>%
      system(intern = TRUE) %>%
      paste(collapse = "\n") %>%
      str_extract("(?<=DexBot, came in rank #)[0-9]")
  }

  system("rm *.hlt")
  RESULTS[[i]] <- list(config, results)
}

saveRDS(RESULTS, file = "cartres.RDS")
sapply(RESULTS[1:72], function(x) table(x[[2]]))
resdf <- lapply(RESULTS[1:72], function(x) as.data.table(x[[1]])) %>%
  rbindlist
resdf[, wins := sapply(RESULTS[1:72], function(x) mean(x[[2]] == "1"))]

resdf[nopp == 1 & dim == 20 & earlygame_max_t != 62][order(earlygame_max_t)]
# 30
resdf[nopp == 3 & dim == 20 & earlygame_decay != 62][order(earlygame_decay)]
# FALSE-ish
resdf[nopp == 1 & dim == 40 & earlygame_order != 3][order(earlygame_order)]
# 5
resdf[nopp == 1 & dim == 40 & earlygame_order != 3][order(earlygame_order)]


resdf[nopp == 1 & dim == 40 & earlygame_max_area != 16][order(earlygame_max_area)]
# 4/8


resdf[nopp == 1 & dim == 40][order(earlygame_all_border)]
# No difference

resdf[nopp == 1 & dim == 40][order(min_wait_turns)]
# 5?
