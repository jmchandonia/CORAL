import { Injector, ErrorHandler, Injectable, NgZone } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';

@Injectable()

export class GlobalErrorHandler implements ErrorHandler {

    constructor(private injector: Injector, private zone: NgZone) {}

    handleError(error: Error | HttpErrorResponse) {

        const router = this.injector.get(Router);

        if (error instanceof HttpErrorResponse) {
            const {status, message} = error;
            this.zone.run(() => router.navigate(['/error', {status, message}]));
            console.error(error);
        }

    }
}
