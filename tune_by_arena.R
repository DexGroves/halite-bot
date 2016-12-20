library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

roi_boost_range = seq(0.5, 3.0, length.out = 100)
warmongery_range = seq(0.2, 2, length.out = 100)
assumed_combat_range = seq(0, 120, length.out = 100)
dist_lim_range = seq(1, 4, length.out = 100)
combat_wait_range = seq(0.5, 3.5, length.out = 100)
noncombat_wait_range = seq(1.5, 6.5, length.out = 100)
max_wait_range = seq(5.5, 9.5, length.out = 100)
min_dpdt_range = seq(0.001, 0.01, length.out = 100)
roi_skew_range = seq(1.2, 3.5, length.out = 100)
blur_sigma_range = seq(2, 8, length.out = 100)
global_exponent_range = seq(0.2, 1.2, length.out = 100)

sample_new_config <- function(N = 1) {
  list(
    roi_boost = sample(roi_boost_range, N, TRUE),
    warmongery = sample(warmongery_range, N, TRUE),
    assumed_combat = sample(assumed_combat_range, N, TRUE),
    dist_lim = sample(dist_lim_range, N, TRUE),
    combat_wait = sample(combat_wait_range, N, TRUE),
    noncombat_wait = sample(noncombat_wait_range, N, TRUE),
    max_wait = sample(max_wait_range, N, TRUE),
    min_dpdt = sample(min_dpdt_range, N, TRUE),
    roi_skew = sample(roi_skew_range, N, TRUE),
    blur_sigma = sample(blur_sigma_range, N, TRUE),
    global_exponent = sample(global_exponent_range, N, TRUE),
    name = paste0("DexBot_", seq(N))
  )
}

build_call <- function(dim, configs) {
  config_args <- paste(paste("\"python3 MyBot.py", configs, "\" "),
                       collapse = " ")
  call <- paste0(
    "halite -t -d ",
    "\"", dim, " ", dim, "\" ",
    config_args
  )
  call
}

# 11s per conf-core
nplayers <- 4
nrounds <- 4
ngame_r1 <- 24
dim <- 40
ncore <- 48

nconfs <- nplayers ^ nrounds

configs <- as.data.frame(sample_new_config(nconfs))
configs$ave_placement <- 0
configs$agg_placement <- 0

for (j in seq(nrow(configs))) {
  cat(j)
  cat("\t")
  as.list(configs[j, ]) %>%
    toJSON(auto_unbox = TRUE, prettify = TRUE) %>%
    cat(file = as.character(configs[j, "name"]))
}

system.time({
registerDoMC(ncore)
for (round in seq(nrounds-1)) {
  cat(paste("ROUND", round, "\n"))

  round_runs <- max(ncore, ngame_r1 * 2 ^ (round - 1))
  for (i in seq(nrow(configs) / nplayers)) {
    min_conf <- (i-1)*nplayers + 1
    max_conf <- (i) * nplayers
    this_confs <- configs[seq(min_conf, max_conf), ]

    cat(paste("\n\tConf. nbr", i, "of", nrow(configs) / nplayers, "\n"))
    call <- build_call(dim, as.character(this_confs$name))
    results <- foreach(i = seq(round_runs), .combine = rbind) %dopar% {
      cat(".")
      system(call, intern = TRUE) %>%
        tail(nplayers) %>%
        sapply(str_extract, "(?<=came in rank #)[0-9]") %>%
        as.numeric
    }
    system("rm *.hlt")
    res <- apply(results, 2, mean)
    configs[seq(min_conf, max_conf),
            "ave_placement"] <- res
    configs[seq(min_conf, max_conf),
            "agg_placement"] <- sapply(seq(nplayers),
                                       function(x) which(order(res) == x))

  }
  saveRDS(configs, file="confs.RDS")
  configs <- configs[configs$agg_placement == 1, ]
}
})
# test <- readRDS(configs, file="confs.RDS")
# test <- test[test$agg_placement == 1, ]
# configs <- test
this_confs <- configs
call <- build_call(dim, as.character(this_confs$name))
results <- foreach(i = seq(1000), .combine = rbind) %dopar% {
  cat(".")
  system(call, intern = TRUE) %>%
    tail(nplayers) %>%
    sapply(str_extract, "(?<=came in rank #)[0-9]") %>%
    as.numeric
}
apply(results, 2, mean)
system("rm *.hlt")
res <- apply(results, 2, mean)
configs <- configs[1:4, ]
configs[, "ave_placement"] <- res
configs[, "agg_placement"] <- sapply(seq(nplayers),
                                   function(x) which(order(res) == x))

}
# dexbot_157
