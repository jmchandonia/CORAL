import { Component, OnInit } from '@angular/core';
import { Select2OptionData } from 'ng2-select2';
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

  processData: Array<Select2OptionData> = [{id: '', text: ''}];
  campaignData: Array<Select2OptionData> = [{id: '', text: ''}];
  personnelData: Array<Select2OptionData> = [{id: '', text: ''}];
  processValue: string;
  requiredProcess = false;
  errorMessages: string[] = [];
  error = false;
  startDateError = false;
  endDateError = false;

  options: Select2Options = {
    width: '100%',
    containerCssClass: 'select2-custom-container',
  };

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
      this.processData = [this.processData[0], ...data.results];
    });
  }

  getCampaignOterms() {
    this.uploadService.getCampaignOterms().subscribe((data: any) => {
      this.campaignData = [this.campaignData[0], ...data.results];
    });
  }

  getPersonnelOterms() {
    this.uploadService.getPersonnelOterms().subscribe((data: any) => {
      this.personnelData = [this.personnelData[0], ...data.results];
    });
  }

  setBrickProcess(event) {
    if (event.value.length) {
      const process = event.data[0];
      this.brick.process = new Term(process.id, process.text);
    }
  }

  setBrickCampaign(event) {
    if (event.value.length) {
      const campaign = event.data[0];
      this.brick.campaign = new Term(campaign.id, campaign.text);
    }
  }

  setBrickPersonnel(event) {
    if (event.value.length) {
      const person = event.data[0];
      this.brick.personnel = new Term(person.id, person.text);
    }
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
