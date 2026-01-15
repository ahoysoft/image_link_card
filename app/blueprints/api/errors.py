"""API error handlers."""

from flask import jsonify


def register_api_error_handlers(bp):
    """Register error handlers for the API blueprint.

    Args:
        bp: The blueprint to register handlers on
    """

    @bp.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'error': 'Bad request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400

    @bp.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401

    @bp.errorhandler(403)
    def forbidden(error):
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403

    @bp.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not found',
            'message': 'The requested resource was not found'
        }), 404

    @bp.errorhandler(422)
    def validation_error(error):
        return jsonify({
            'error': 'Validation error',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid data'
        }), 422

    @bp.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429

    @bp.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'error': 'Internal server error',
            'message': 'An unexpected error occurred'
        }), 500
