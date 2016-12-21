library("jsonlite")
library("magrittr")
library("stringr")
library("foreach")
library("doMC")

assumed_cstrn_range = c(5, 10, 25, 80)
wait_ratio_range = c(3, 5, 7)
value_t2a_exp_range = c(1.5, 2, 2.5)
terr_multi_range = c(5, 10, 15, 25)
terr_t2a_multi_range = c(1, 2, 5)
terr_intercept_range = c(50, 100, 250)
enemy_multi_range = c(1, 1.3, 1.8)
danger_close_multi_range = c(3.0, 6.5, 10.0)

sample_new_config <- function(N = 1) {
  list(
    assumed_cstrn = sample(assumed_cstrn_range, N, TRUE),
    wait_ratio = sample(wait_ratio_range, N, TRUE),
    value_t2a_exp = sample(value_t2a_exp_range, N, TRUE),
    terr_multi = sample(terr_multi_range, N, TRUE),
    terr_t2a_multi = sample(terr_t2a_multi_range, N, TRUE),
    terr_intercept = sample(terr_intercept_range, N, TRUE),
    enemy_multi = sample(enemy_multi_range, N, TRUE),
    danger_close_multi = sample(danger_close_multi_range, N, TRUE),
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
