import { Injector, ErrorHandler, Injectable, NgZone } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

@Injectable()

export class GlobalErrorHandler implements ErrorHandler {

    private router: Router;

    constructor(private injector: Injector, private zone: NgZone) {
        setTimeout(() => {
            this.router = this.injector.get(Router);
        });
    }

    handleError(error: Error | HttpErrorResponse) {

        if (error instanceof HttpErrorResponse) {
            const {status, message} = error;
            this.zone.run(() => this.router.navigate(['/error', {status, message}]));
            console.error(error);
        } else {
            this.zone.run(() => this.router.navigate(['/error', {message: error.message}]));
            console.error(error);
        }

    }
}
