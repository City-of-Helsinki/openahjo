#include <stdlib.h>
#include <stdio.h>
#include <assert.h>

#include <malaga.h>

char *stem_word(const char *s)
{
    value_t res;
    char *ret;

    analyse_item(s, MORPHOLOGY);
    res = first_analysis_result();
    if (res == NULL)
        return NULL;
    assert(get_value_type(res) == STRING_SYMBOL);
    ret = get_value_string(res);
    return ret;
}

int stem_string(const char *s, char ***out)
{
    return 0;
}

int stem_init(const char *project_path)
{
    init_libmalaga(project_path);
    return 0;
}

void stem_finish(void)
{
    terminate_libmalaga();    
}

#ifdef TEST
int main()
{
    char **res, *p;
    int n, i;

    stem_init("sukija/suomi.pro");
    printf("%s\n", stem_word("kiviniemen"));
}
#endif
