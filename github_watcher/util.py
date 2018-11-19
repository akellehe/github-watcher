import logging


def raise_value_error(parser, parameter_name):
    parser.print_help()
    raise ValueError("--{} is required for the check action".format(parameter_name))


def validate_args(parser):
    args = parser.parse_args()
    if args.repo is None:
        raise_value_error(parser, 'repo')
    if args.user is None:
        raise_value_error(parser, 'user')
    if args.filepath is None:
        raise_value_error(parser, 'filepath')


def read_access_token(parser):
    args = parser.parse_args()
    try:
        with open(args.access_token_file, 'rb') as github_auth_fp:
            return github_auth_fp.read().decode('utf-8').strip()
    except IOError as e:
        logging.info("You must store your github access token at ~/.github.")
        logging.info("  1. Go to your github site (e.g. github.com) and")
        logging.info("  2. click your avatar in the top right then")
        logging.info("  3. click Settings then")
        logging.info("  4. click Personal access tokens on the left then")
        logging.info("  5. Generate access token then")
        logging.info("  6. click repo and user permissions checkboxes. next")
        logging.info("  7. click Generate Token. ")
        logging.info("  8. SAVE THAT. copy/paste to ~/.github you will never see it again.")
        raise ValueError(">> github-watcher --help for more information")
