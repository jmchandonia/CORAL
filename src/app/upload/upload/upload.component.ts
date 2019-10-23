import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';

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
    'data-values',
    'dimensions',
    'load',
    'validate',
    'map',
    'preview',
    'create'
  ];

  progressIndex = 0;

  constructor(
    private router: Router
  ) {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.currentUrl = event.url.split('/').pop();
        this.progressIndex = this.uploadSteps.indexOf(this.currentUrl);
      }
    });
  }

  ngOnInit() { }

  getProgressStatus(index) {
    if (index === this.progressIndex) {
      return 'active';
    }
    return index > this.progressIndex ? 'incomplete' : 'complete';
  }

  format(step) {
    return (step.charAt(0).toUpperCase() + step.slice(1)).replace('-', ' ');
  }

  nextStep() {
    if(this.progressIndex == 4) {
      this.progressIndex = 7;
    } else {
      this.progressIndex++;
    }
    this.router.navigate([`/upload/${this.uploadSteps[this.progressIndex]}`]);
  }

  previousStep() {
    this.progressIndex--;
    this.router.navigate([`/upload/${this.uploadSteps[this.progressIndex]}`]);
  }

}
