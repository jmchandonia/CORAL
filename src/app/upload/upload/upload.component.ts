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
    'dimensions',
    'load',
    'validate',
    'map',
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

  capitalize(step) {
    return step.charAt(0).toUpperCase() + step.slice(1);
  }

  nextStep() {
    this.progressIndex++;
    this.router.navigate([`/upload/${this.uploadSteps[this.progressIndex]}`]);
  }

  previousStep() {
    this.progressIndex--;
    this.router.navigate([`/upload/${this.uploadSteps[this.progressIndex]}`]);
  }

}
