import emailjs from '@emailjs/browser';

const SERVICE_ID = process.env.NEXT_PUBLIC_EMAILJS_SERVICE_ID || 'service_ipbsw96';
const TEMPLATE_ID = process.env.NEXT_PUBLIC_EMAILJS_TEMPLATE_ID || 'template_3pws1rj';
const PUBLIC_KEY = process.env.NEXT_PUBLIC_EMAILJS_PUBLIC_KEY || 'cyv9GNLfabpJkFHrn';

export const sendWelcomeEmail = async (email: string, fullName: string) => {
  try {
    // We send multiple variations of the variable names just in case 
    // the user used different placeholders in their EmailJS template (e.g. {{to_name}} vs {{user_name}})
    const templateParams = {
      to_email: email,
      to_name: fullName,
      user_email: email,
      user_name: fullName,
      full_name: fullName,
      email: email,
      message: 'Welcome to Smart Academic! We are thrilled to have you on board as you unlock your full academic potential.'
    };

    const response = await emailjs.send(SERVICE_ID, TEMPLATE_ID, templateParams, PUBLIC_KEY);
    console.log('Welcome email sent successfully:', response.status, response.text);
    return true;
  } catch (error) {
    console.error('Failed to send welcome email:', error);
    return false;
  }
};

