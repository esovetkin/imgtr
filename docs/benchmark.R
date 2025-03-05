require("ggplot2")
require("Hmisc")
require("scales")

df <- read.csv("benchmark.csv.gz")

get_ci <- function(df)
{
    cols <- c("HD_SZS19.cells", "HD_SZS19.cells_shapeokay", "HD_SZS19.cells_0", "HD_SZS19.cells_0_shapeokay")
    d <- lapply(unique(df$type), function(type) {
        d <- df[df$type == type,]
        x <- as.data.frame(binconf(colSums(d[cols]), nrow(d), alpha=0.1))
        x$cols <- cols
        x$type <- type
        x
    })
    d <- do.call(rbind,d)
    rownames(d) <- 1:nrow(d)
    d
}

trans_perc <- trans_new(
  name      = "quadratic",
  transform = function(x) x^3,
  inverse   = function(x) x^(1/3),
  format    = percent_format(),
  domain    = c(0, Inf)
)

png("success_rate.png", width=3000, height=2000, res=300)
d <- get_ci(df)
ggplot(d[d$cols %in% c("HD_SZS19.cells", "HD_SZS19.cells_0", "HD_SZS19.cells_0_shapeokay"),], aes(x=type,y=PointEst)) +
    geom_point() +
    geom_errorbar(aes(ymin=Lower, ymax=Upper)) +
    scale_y_continuous(breaks=round(seq(0,1,length.out=21)^(1/3),4), trans=trans_perc) +
    ylab("success rate") + xlab("image source") + facet_grid(cols = vars(cols)) +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))
dev.off()

png("rmse.png", width=3000, height=2000, res=300)
ggplot(df[,c("type","HD_SZS19.cells_0_rmse")], aes(x=type,y=HD_SZS19.cells_0_rmse)) +
    geom_boxplot() +
    scale_y_continuous(breaks=0.1 * 2^(1:10), trans="log2") +
    ylab("reprojection error") + xlab("image source") +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))
dev.off()

d <- get_ci(df[grep("MCLB", df$fn),])
ggplot(d[d$cols %in% c("HD_SZS19.cells", "HD_SZS19.cells_0", "HD_SZS19.cells_0_shapeokay"),], aes(x=type,y=PointEst)) +
    geom_point() +
    geom_errorbar(aes(ymin=Lower, ymax=Upper)) +
    scale_y_continuous(breaks=round(seq(0,1,length.out=21)^(1/3),4), trans=trans_perc) +
    ylab("success rate") + xlab("image source") + facet_grid(cols = vars(cols)) +
    theme(axis.text.x = element_text(angle = 90, vjust = 0.5, hjust=1))
