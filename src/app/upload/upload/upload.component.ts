import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { environment } from 'src/environments/environment';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css']
})
export class UploadComponent implements OnInit {

  currentUrl: string;
  public uploadSteps = [
    'type',
    'properties',
    'data-variables',
    'dimensions',
    'load',
    'validate',
    'preview',
    'create'
  ];

  progressIndex = 0;
  maxStep = 0;

  constructor(
    private router: Router,
    private validator: UploadValidationService,
  ) {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.currentUrl = event.url.split('/').pop();
        this.progressIndex = this.uploadSteps.indexOf(this.currentUrl);
        if (this.progressIndex < 0) {
          this.progressIndex = 0;
          this.currentUrl = 'type';
        }
      }
    });
  }

  ngOnInit() {
    this.maxStep = this.progressIndex;
  }

  getProgressStatus(index) {
    if (index === this.progressIndex) {
      return 'active';
    }
    if (environment.production) {
      return index > this.maxStep ? 'incomplete' : 'complete';
    } else {
      return index > this.progressIndex ? 'incomplete' : 'complete';
    }
  }

  format(step) {
    return (step.charAt(0).toUpperCase() + step.slice(1)).replace('-', ' ');
  }

  nextStep() {
    if (!this.validator.validationErrors(this.currentUrl)) {
      this.progressIndex++;
      if (this.progressIndex > this.maxStep) {
        this.maxStep = this.progressIndex;
        }
      this.router.navigate([`/upload/${this.uploadSteps[this.progressIndex]}`]);
    }
  }

  previousStep() {
    this.progressIndex--;
    this.router.navigate([`/upload/${this.uploadSteps[this.progressIndex]}`]);
  }

  navigateBreadcrumb(step: string, index: number) {
    // prod environment check is used to facilitate dev debugging (developer won't need to navigate throubgh steps)
    if (index <= this.maxStep || !environment.production) {
      this.router.navigate([`/upload/${step}`]);
    }
  }

}
