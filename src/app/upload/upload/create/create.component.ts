import { Component, OnInit } from '@angular/core';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, Term } from 'src/app/shared/models/brick';
import { NgxSpinnerService } from 'ngx-spinner';
import { BsDatepickerConfig } from 'ngx-bootstrap/datepicker';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

@Component({
  selector: 'app-create',
  templateUrl: './create.component.html',
  styleUrls: ['./create.component.css']
})
export class CreateComponent implements OnInit {

  constructor(
    private uploadService: UploadService,
    private spinner: NgxSpinnerService,
    private validator: UploadValidationService
  ) { }

  loading = false;
  successId: string;

  datepickerConfig: Partial<BsDatepickerConfig> = { containerClass: 'theme-dark-blue' };

  processData: Array<Term> = [];
  campaignData: Array<Term> = [];
  personnelData: Array<Term> = [];
  processValue: string;
  requiredProcess = false;
  errorMessages: string[] = [];
  error = false;
  startDateError = false;
  endDateError = false;
  brick: Brick;

  ngOnInit() {
    this.brick = this.uploadService.getBrickBuilder();
    this.requiredProcess = this.uploadService.requiredProcess;

    if (this.requiredProcess) {
      this.processData = [this.brick.process];
      this.processValue = this.brick.process.id;
    } else {
      this.getProcessOterms();
    }

    this.getCampaignOterms();
    this.getPersonnelOterms();
  }

  getProcessOterms() {
    this.uploadService.getProcessOterms().subscribe((data: any) => {
      this.processData = [...data.results];
    });
  }

  getCampaignOterms() {
    this.uploadService.getCampaignOterms().subscribe((data: any) => {
      this.campaignData = [...data.results];
    });
  }

  getPersonnelOterms() {
    this.uploadService.getPersonnelOterms().subscribe((data: any) => {
      this.personnelData = [...data.results];
    });
  }

  setBrickProcess(event: Term) {
    this.brick.process = event;
  }

  setBrickCampaign(event: Term) {
    this.brick.campaign = event;
  }

  setBrickPersonnel(event: Term) {
    this.brick.personnel = event;
  }

  submitBrick() {
    const errors = this.validator.validateCreateStep()
    this.errorMessages = errors.messages;
    if (!this.errorMessages.length) {
      this.loading = true;
      this.spinner.show();
      this.uploadService.submitBrick()
        .subscribe((data: any) => {
          this.loading = false;
          this.spinner.hide();
          this.successId = data.results;
          this.startDateError = false;
          this.endDateError = false;
      });
    } else {
      this.error = true;
      this.startDateError = errors.startDateError;
      this.endDateError = errors.endDateError;
    }
  }
}
