library(dplyr)

# Pede ao usuario um arquivo de input
input <- file.choose()
dados <- read.delim2(file = input)

# Remove empty boxes (since log(10) cannot be calculated).
# It is important to note that if the largest box has a 0 count, then all smaller boxes will have 0 count.
# The opposite is also true (if count is 1 for the largest box, then all boxes will have at least 1 count)
val_dados <- dados[dados$boxcount != 0,]
box_id <- integer()
fractal_dimension <- double()
r_squared <- double()
boxes <- unique(val_dados$Id)

for (box in boxes){
    box_id <- append(box_id, box)
    regr_line <- lm(log10(boxcount) ~ log10(box_size), data = val_dados[val_dados$Id == box,])
    fractal_dimension <- append(fractal_dimension, regr_line$coefficients[2] * -1)
    r_squared <- append(r_squared, summary.lm(regr_line)$r.squared)
}

frac_dim <- data.frame(box_id, fractal_dimension, r_squared)
print(frac_dim)

# Pede ao usuario o nome do arquivo de output. Como padrao, salva no mesmo diretorio do script
output <- readline(prompt = "Digite o nome do arquivo de saida: ")
write.table(frac_dim, file = output, dec = ',', row.names = FALSE, col.names = TRUE)
